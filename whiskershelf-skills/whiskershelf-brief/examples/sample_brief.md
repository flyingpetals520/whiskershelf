# 灵感碰撞:SpikeGPT × Spikformer × RWKV-7

> 生成时间: 2026-06-06 14:23
> 选中论文: 3 篇
> 用户补充上下文: 想做面向边缘部署的高效序列模型

## 1. 共同主题与方法张力
三篇都关注长序列建模的低开销方案,但 SNN 路线(SpikeGPT, Spikformer)受限于脉冲不可微,RWKV-7 走线性注意力获得了更好的工程化生态。

## 2. 研究方向

### 方向 1: 把 RWKV-7 的状态演化机制迁移到脉冲域
**核心 Idea**: 用 RWKV-7 的 channel-wise 状态衰减代替 Spikformer 的膜电位衰减,实现"按需发射"的稀疏脉冲序列。
**方法迁移路径**: 以 Spikformer 的 SSA(spike self-attention)为骨架,替换 token-mix 子层为 RWKV-7 的 WKV 算子,神经元仍为 IF,但 LIF 衰减改用 RWKV-7 的对数衰减。
**预期难点**: 1) RWKV-7 的状态依赖输入,脉冲编码后状态更新会变稀疏;2) 替代梯度在 RWKV 衰减项上不稳定。
**验证方案**: 在 CIFAR-10-DVS / N-Caltech-101 上对比 Spikformer 基线,测量能效比(ops/J)和 Top-1。
**可能的跨域跳跃**: 金融时序预测、IMU 动作识别。

### 方向 2: 借鉴 RWKV-7 的 Gooselike 状态做时序脉冲去噪
**核心 Idea**: 把 RWKV-7 的 data-dependent decay 用作 SNN 输入编码阶段的脉冲清洗器。
**方法迁移路径**: 在 SpikeGPT 编码器前端加一层 RWKV-Gate,清洗冗余脉冲,再进入 SNN 主干。
**预期难点**: 延迟增加是否能被稀疏性收益抵消。
**验证方案**: 在 Speech Commands 上测稀疏度-精度曲线。

### 方向 3: 跨模态:脉冲 + 线性注意力的统一框架
**核心 Idea**: 把 SNN 的时序优势与线性注意力的长程依赖融合,作为多模态基础架构候选。
**方法迁移路径**: 双分支结构,视觉走 Spikformer,文本走 RWKV-7,中间用 cross-attention spike token 桥接。
**预期难点**: 模态间时间尺度对齐。
**验证方案**: 在 N-Caltech-101 + TinyStories 上做小规模对齐实验。

## 3. 跨域跳跃建议
- 把同款稀疏状态机制迁移到 LLM 推理 KV-cache 压缩
- 借鉴 SNN 的事件驱动特性,做面向低功耗 AR 眼镜的 always-on 视觉前端

## 4. 风险与盲点
- SNN + Linear Attention 的工程化工具链薄弱,可能要自己写很多 CUDA
- RWKV-7 的 decay 引入后,反向传播的 surrogate gradient 设计空间很大,可能做 2-3 轮才能收敛

## 思考过程
```text
The model thought about it... 思考过程...
```
