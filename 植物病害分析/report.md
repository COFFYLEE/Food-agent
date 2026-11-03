# Leaf Disease Classification on PlantVillage

**COMP9444 Group Project.** We build and compare image classifiers for plant-leaf disease
diagnosis, and ask whether the model is cheap enough to deploy in the field and whether it
attends to the disease rather than the background.

## 1. Introduction

Automatic leaf-disease diagnosis can help growers catch problems early — ideally on a phone
in the field, not a server. We use the PlantVillage dataset (close-up leaf photos, one folder
per class) and frame the task as classification over **38 disease classes**. We answer two
main questions — *how much does transfer learning help?* and *is the model small and fast
enough to deploy?* — and use Grad-CAM to check the model looks at the lesion. We also include a
brief check of whether handling the class imbalance changes anything.

## 2. Data and exploratory analysis

The dataset ships 39 folders. One, `Background_without_leaves`, holds random non-leaf photos;
it is a reject class, not a disease, so we exclude it and keep the **38 disease classes**
(~54,000 images). Two properties drive our design:

- **Severe class imbalance (~36×).** The largest class has ~3,855 training images, the
  smallest (`Potato___healthy`) only ~106. Plain accuracy could look good while the rare
  classes fail, so we adopt **macro-F1** (the unweighted mean of per-class F1) as the headline
  metric, and we split the data with **stratification** so every class keeps its proportions
  across train/validation/test (70/15/15, fixed seed).
- **Clean, controlled images.** The photos are close-up single leaves on plain backgrounds, so
  high accuracy is expected; the interesting questions are comparative.

## 3. Related work

Deep learning is the standard approach to leaf-disease classification, and the PlantVillage
dataset is its most common benchmark. **Mohanty et al. (2016)** [1] trained AlexNet and
GoogLeNet on the 54,306-image PlantVillage collection and reached 99.35% accuracy under
controlled conditions — but importantly cautioned that accuracy fell sharply when the model
was tested on images captured under different, real-world conditions, foreshadowing the
lab-to-field gap. **Ferentinos (2018)** [2] extended this across five architectures and 58
plant/disease classes on a larger 87,848-image set, with the best model (VGG) reaching
99.53%. **Geetharamani and Pandian (2019)** [3], who released the exact 39-class dataset we
use, reported 96.46% with a purpose-built nine-layer CNN.

The consistent theme in this prior work is a **saturated benchmark**: accuracy on clean,
single-leaf PlantVillage images is already above 99%, so simply pushing the number higher
adds little. The open limitations are elsewhere — whether the reported accuracy reflects the
disease rather than a background shortcut, and whether a model is small and fast enough to run
outside a lab. Our work targets those gaps: we quantify the accuracy/deployability trade-off
with a mobile network (**MobileNetV3-Small** [5], built on efficient depthwise-separable
convolutions), we use **ResNet18** [4] as a strong transfer-learning reference, and we apply
**Grad-CAM** [6] to check the model attends to lesions rather than the controlled background.

## 4. Method

**Models** (identical data and preprocessing):

1. **SimpleCNN** — a compact from-scratch network (four `Conv-BN-ReLU-MaxPool` blocks, global
   average pool, one linear layer; ~0.4M parameters). Our baseline.
2. **ResNet18** — ImageNet-pretrained, final layer replaced with a 38-way head, whole network
   fine-tuned (~11.2M parameters). The strong transfer-learning model.
3. **MobileNetV3-Small** — a mobile-first network fine-tuned the same way (~1.6M parameters).
   The candidate for deployment.

**Training.** Adam and cross-entropy for a few epochs (12 for the baseline, 8 for the
pretrained models), keeping the weights with the best **validation** macro-F1. The **test set
is used once**, for the final numbers. Augmentation is light (random crop, flip, mild colour
jitter); evaluation is deterministic. Models are cached after training so the notebook can be
re-run without retraining.

**Deployment measure.** We report **CPU** single-image latency, parameter count, and on-disk
size, because a field/on-device model runs on a CPU or phone — not a datacenter GPU.

**Imbalance handling.** We retrain ResNet18 with **class-weighted cross-entropy** (inverse
frequency) and compare to the plain model, watching recall on the rarest classes.

## 5. Results

All numbers are on the held-out test set (8,146 images).

| Model | Accuracy | Macro-F1 | Params | Size | CPU latency |
|---|---|---|---|---|---|
| SimpleCNN (from scratch) | 96.82% | 95.48% | 0.4M | 1.6 MB | 29.7 ms |
| ResNet18 (fine-tuned) | 99.29% | 99.07% | 11.2M | 44.8 MB | 40.0 ms |
| MobileNetV3-Small (fine-tuned) | **99.35%** | **99.11%** | 1.6M | **6.2 MB** | **5.1 ms** |

**Transfer learning wins clearly.** The two fine-tuned models improve macro-F1 by ~3.6 points
over the from-scratch CNN and cut test errors about four-and-a-half-fold (roughly 58 vs 259
errors of 8,146). Pretrained features are the single biggest contributor to accuracy. For all
models macro-F1 sits next to accuracy, so performance is uniform across classes, not carried by
the common ones.

**MobileNet is the best all-round choice.** On this run MobileNetV3-Small marginally beats
ResNet18 on both accuracy (99.35% vs 99.29%) and macro-F1 (99.11% vs 99.07%) — a gap well
within single-seed noise, so treat the two as tied at the top — while being about **7× smaller**
and **~8× faster on the CPU** (5.1 ms vs 40.0 ms per image). Two observations sharpen the point:
parameter count is *not* speed — the tiny SimpleCNN is ~6× slower on CPU than MobileNet because
its dense convolutions run at full resolution, whereas MobileNet's depthwise-separable design is
built for cheap CPU inference; and the ranking is measured on **CPU deliberately**, since a GPU
(which a field device lacks) would order the models differently. (Absolute CPU latency is
hardware- and thread-dependent; the 7.2× size ratio is exact, and MobileNet's several-fold CPU
speed advantage is the robust, repeatable finding.)

As a brief robustness check, we also trained ResNet18 with class-weighted loss; it **improved
recall on the rarest ten classes** (98.4% → 99.8%) but slightly lowered overall accuracy and
macro-F1 (to 99.15% / 98.93%) — a minor trade-off, not a free win, and it does not raise the
headline metric. The residual errors are the **Corn Gray Leaf Spot vs Northern Leaf Blight**
pair (~8% of that class), two look-alike diseases — a matter of visual *similarity*, not class
*rarity*, which reweighting cannot fix, so we keep plain training as the default.

**The model looks at the disease.** Grad-CAM on the deployment model places its evidence on the
leaf and the lesion (e.g. the powdery-mildew patch, the cedar-rust spot), with the background
left cold — so the high accuracy reflects the task, not a background shortcut.

**Comparison to prior work.** Our ~99.3% accuracy is in line with published PlantVillage
results (99.35% [1], 99.53% [2], 96.46% [3]), which is expected on this saturated benchmark.
Our contribution is not a higher number but the deployability result (a mobile model at
near-identical accuracy) and the honest imbalance and interpretability analysis.

## 6. Discussion and conclusion

For a field tool we recommend **fine-tuned MobileNetV3-Small**: on this run it is the best model
on every axis — accuracy (99.35%), macro-F1 (99.11%), size, and CPU speed — at ~1/7 the size and
~1/8 the CPU latency of ResNet18, so it is the one that could actually run in real time on a
phone. Two clear findings support the study — transfer learning gives a large boost over training
from scratch, and a mobile architecture buys deployability almost for free — and Grad-CAM
confirms the model is lesion-based. A brief check found that class weighting improves rare-class
recall but slightly lowers the overall metrics, so the imbalance is not the headline bottleneck.

**Limitations.** Results come from a single training run (one seed), so the small differences
between the near-ceiling models should be read as indicative rather than exact. More
importantly, PlantVillage images are clean laboratory
photographs; a field-deployed model would face cluttered backgrounds and varied lighting and
would very likely score lower. The Corn look-alike confusion is the clearest sign that the
ceiling here is set by the data, not the model.

## References

[1] S. P. Mohanty, D. P. Hughes, and M. Salathé, "Using deep learning for image-based plant
disease detection," *Frontiers in Plant Science*, vol. 7, art. 1419, 2016.

[2] K. P. Ferentinos, "Deep learning models for plant disease detection and diagnosis,"
*Computers and Electronics in Agriculture*, vol. 145, pp. 311–318, 2018.

[3] G. Geetharamani and A. Pandian, "Identification of plant leaf diseases using a nine-layer
deep convolutional neural network," *Computers & Electrical Engineering*, vol. 76,
pp. 323–338, 2019.

[4] K. He, X. Zhang, S. Ren, and J. Sun, "Deep residual learning for image recognition," in
*Proc. IEEE Conf. Computer Vision and Pattern Recognition (CVPR)*, 2016, pp. 770–778.

[5] A. Howard et al., "Searching for MobileNetV3," in *Proc. IEEE/CVF Int. Conf. Computer
Vision (ICCV)*, 2019, pp. 1314–1324.

[6] R. R. Selvaraju et al., "Grad-CAM: Visual explanations from deep networks via
gradient-based localization," in *Proc. IEEE Int. Conf. Computer Vision (ICCV)*, 2017,
pp. 618–626.
