"""可编辑的像素路径：颜色提供观测，锚点确定身份，排除区保留缺失证据。

本模块不读取坐标轴文字，不推断 Sij。全局代价路径允许交叉和陡峭陷波；
遮挡没有足够像素时保留缺列，人工锚点只代表用户明确提供的位置。
"""

# Codex说明(自动生成)： 从 __future__ 导入 annotations，启用较新的类型标注行为，减少运行期导入或前向引用问题。
from __future__ import annotations

# Codex说明(自动生成)： 导入 numpy as np，执行数组、向量化和数值仿真计算。
import numpy as np


# 统一验证原图矩形，禁止负索引或退化范围进入 NumPy 切片。
def checked_box(box, shape):
    # 几何坐标均为原图像素，人工矩形只能在完整图像内部。
    values = np.asarray(box, dtype=float)
    # Codex说明(自动生成)： 检查条件 values.shape != (4,) or not np.isfinite(values).all() o...，根据结果选择后续执行路径。
    if (
        values.shape != (4,)
        or not np.isfinite(values).all()
        or not np.equal(values, np.rint(values)).all()
    ):
        # Codex说明(自动生成)： 抛出 ValueError('图框需要四个整数像素坐标。')，明确提示输入、状态或处理流程无法继续。
        raise ValueError("图框需要四个整数像素坐标。")
    # 坐标已通过有限整数验证，转换后用于数组边界。
    left, top, right, bottom = map(int, values)
    # Codex说明(自动生成)： 检查条件 not (0 <= left < right < shape[1] and 0 <= top < bottom...，根据结果选择后续执行路径。
    if not (0 <= left < right < shape[1] and 0 <= top < bottom < shape[0]):
        # Codex说明(自动生成)： 抛出 ValueError('图框超出图片或没有有效面积。')，明确提示输入、状态或处理流程无法继续。
        raise ValueError("图框超出图片或没有有效面积。")
    # 返回经过验证的矩形，调用方可安全使用闭区间边界。
    return left, top, right, bottom


# 从像素观测追踪一条用户指定身份的曲线，同时返回逐点证据类别。
def trace_pixel_path(rgb, box, colour, anchors=(), exclusions=()):
    # 从 RGB 中消除白色抗锯齿的亮度分量，比较色彩方向而不是绝对亮度。
    left, top, right, bottom = checked_box(box, rgb.shape)
    # 将图框内 RGB 转为浮点，避免无符号像素减法溢出。
    values = np.asarray(rgb[top : bottom + 1, left : right + 1], dtype=float)
    # 逐像素减去最小 RGB 分量，分离白底抗锯齿的亮度影响。
    chroma = values - values.min(axis=2)[..., None]
    # 色度向量长度衡量像素是否有足够颜色信息。
    strength = np.linalg.norm(chroma, axis=2)
    # 对色度方向归一化，使深色和浅色边缘可比较。
    directions = chroma / np.maximum(strength[..., None], 1)
    # 把取色值转换为浮点向量，后续颜色比较不发生整数截断。
    colour = np.asarray(colour, dtype=float)
    # Codex说明(自动生成)： 检查条件 colour.shape != (3,) or not np.isfinite(colour).all() o...，根据结果选择后续执行路径。
    if (
        colour.shape != (3,)
        or not np.isfinite(colour).all()
        or np.any((colour < 0) | (colour > 255))
    ):
        # Codex说明(自动生成)： 抛出 ValueError('目标颜色必须包含三个 0–255 的 RGB 值。')，明确提示输入、状态或处理流程无法继续。
        raise ValueError("目标颜色必须包含三个 0–255 的 RGB 值。")
    # 从目标颜色扣除白色分量，使取色可匹配同色抗锯齿边缘。
    target = colour - colour.min()
    # 无明显色度时改用灰阶亮度匹配；网格仍由人工排除。
    if np.linalg.norm(target) < 8:
        # 灰黑线使用亮度误差；人工遮罩负责排除同样灰黑的坐标轴与文字。
        distance = np.abs(values.mean(axis=2) - colour.mean()) / 255
        # 记录符合目标颜色的像素，排除区随后从此集合扣除。
        mask = (values.max(axis=2) - values.min(axis=2) < 12) & (distance < 0.12) & (values.max(axis=2) <= 240)
    # Codex说明(自动生成)： 处理前面条件都未命中时的默认分支。
    else:
        # 只比较色度方向，避免把同一条线的深浅边缘拆成多个身份。
        target /= np.linalg.norm(target)
        # 颜色距离仅作为候选筛选证据，不作为识别概率。
        distance = np.linalg.norm(directions - target, axis=2)
        # 记录符合目标颜色的像素，排除区随后从此集合扣除。
        mask = (strength > 12) & (distance < 0.22)
    # 保留排除区域约束，人工辅助放宽颜色时仍遵守此遮罩。
    allowed = np.ones(mask.shape, dtype=bool)
    # 每个排除框仅改变算法遮罩，原图字节保持不变。
    for rectangle in exclusions:
        # 排除区只修改观测遮罩，不擦写原图；横跨曲线时会留下可复核缺列。
        x1, y1, x2, y2 = checked_box(rectangle, rgb.shape)
        # 计算排除框与图框的交集，再转换为局部数组坐标。
        xa, xb, ya, yb = (
            max(x1, left) - left,
            min(x2, right) - left,
            max(y1, top) - top,
            min(y2, bottom) - top,
        )
        # 只有实际覆盖图框的排除区才改变可用像素。
        if xa <= xb and ya <= yb:
            # 从严格颜色观测中移除排除框内的文字或其他干扰。
            mask[ya : yb + 1, xa : xb + 1] = False
            # 同时约束后续人工辅助候选，防止放宽颜色时恢复已排除像素。
            allowed[ya : yb + 1, xa : xb + 1] = False
    # 人工锚点使用原图像素坐标，允许亚像素纵坐标。
    points = np.asarray(anchors, dtype=float).reshape(-1, 2)
    # 限制交互输入规模，同时拒绝 NaN 和无穷坐标。
    if len(points) > 256 or not np.isfinite(points).all():
        # Codex说明(自动生成)： 抛出 ValueError('每条线最多 256 个有限像素锚点。')，明确提示输入、状态或处理流程无法继续。
        raise ValueError("每条线最多 256 个有限像素锚点。")
    # 未加锚点时保留纯像素候选；有锚点时检查其几何一致性。
    if len(points):
        # 按横坐标排序，用户点击顺序不改变曲线的频率顺序。
        points = points[np.argsort(points[:, 0])]
        # 同列多个锚点没有唯一函数值，越界锚点也不能用于校准。
        if np.any(np.diff(np.rint(points[:, 0])) <= 0) or np.any(
            (points[:, 0] < left)
            | (points[:, 0] > right)
            | (points[:, 1] < top)
            | (points[:, 1] > bottom)
        ):
            # Codex说明(自动生成)： 抛出 ValueError('锚点须在图框内，且不能在同一像素列设置两个锚点。')，明确提示输入、状态或处理流程无法继续。
            raise ValueError("锚点须在图框内，且不能在同一像素列设置两个锚点。")
    # 冻结严格颜色观测，用于区分人工辅助样本的证据来源。
    observed_mask = mask.copy()
    # 限制交互输入规模，同时拒绝 NaN 和无穷坐标。
    if len(points) >= 2 and np.ptp(colour) >= 8:
        # JPEG 色度混合可能毁掉颜色身份。只在锚点之间的窄带内放宽观测，
        # 此类点明确标为 manual_guided，不能冒充独立识别到的颜色证据。
        xs = np.arange(left, right + 1)
        # 在相邻人工锚点之间做分段直线引导，不替代实际像素值。
        guide = np.interp(xs, points[:, 0], points[:, 1]) - top
        # 锚点之间只在图框高度 2% 的窄带内放宽颜色候选。
        corridor = abs(np.arange(bottom - top + 1)[:, None] - guide[None, :]) <= max(
            3, (bottom - top) * 0.02
        )
        # 禁止把锚点直线水平延长到未经用户约束的频段。
        corridor &= ((xs >= points[0, 0]) & (xs <= points[-1, 0]))[None, :]
        # 将窄带内较弱颜色证据加入候选；结果必须保留人工辅助标记。
        mask |= corridor & allowed & (strength > 12) & (distance < 0.7)
    # 将每个手工锚点绑定到唯一原图像素列。
    anchor_map = {int(round(x - left)): float(y - top) for x, y in points}
    # 只保存有观测或明确人工锚点的列，不补造缺失列。
    columns = []
    # 按原图每个频率像素列提取候选截面。
    for x in range(right - left + 1):
        # 连续像素段是一项观测；均值按色度加权，减小浅色边缘的影响。
        rows = np.flatnonzero(mask[:, x])
        # 把竖向相邻像素分为色线截面，避免每个抗锯齿像素成为独立候选。
        groups = (
            np.split(rows, np.flatnonzero(np.diff(rows) > 1) + 1) if rows.size else []
        )
        # 每个截面记录中心高度、颜色代价及是否依赖人工辅助。
        observations = [
            (
                float(np.average(group, weights=np.maximum(strength[group, x], 1))),
                float(np.min(distance[group, x])) / 0.22,
                np.any(~observed_mask[group, x]),
            )
            for group in groups
        ]
        # 用户明确指定的坐标优先，其来源记为人工锚点。
        if x in anchor_map:
            # 每个截面记录中心高度、颜色代价及是否依赖人工辅助。
            observations = [(anchor_map[x], 0.0, True)]
        # 候选过密时停止，避免整片文字或噪声触发二次方路径开销。
        if len(observations) > 64:
            # Codex说明(自动生成)： 抛出 ValueError('目标色候选过密，请框选区域或增加排除区。')，明确提示输入、状态或处理流程无法继续。
            raise ValueError("目标色候选过密，请框选区域或增加排除区。")
        # 没有任何像素支持的列保持缺失，后续导出必须披露该缺口。
        if observations:
            # 保存有效列及其候选，保留原始横坐标以识别缺列。
            columns.append((x, np.asarray(observations)))
    # 至少需要两个不同频率位置才能构造曲线。
    if len(columns) < 2:
        # Codex说明(自动生成)： 抛出 ValueError('选定颜色没有足够像素；请调整选色或锚点。')，明确提示输入、状态或处理流程无法继续。
        raise ValueError("选定颜色没有足够像素；请调整选色或锚点。")
    # 记录每列候选的最优前驱，用于最后的路径回溯。
    states = []
    # 保留前一有效列的代价和像素行坐标。
    previous = None
    # 沿频率方向累计颜色与几何代价，不按高低关系强制分线。
    for x, observations in columns:
        # 同一身份全局累计颜色误差与几何距离；不强制 y 排序，因此允许交叉。
        emission = observations[:, 1].copy()
        # 限制交互输入规模，同时拒绝 NaN 和无穷坐标。
        if len(points) >= 2 and points[0, 0] <= x + left <= points[-1, 0]:
            # 只在用户两侧锚点之间约束身份；不把端点水平外推到整幅图。
            guide = np.interp(x + left, points[:, 0], points[:, 1]) - top
            # 软约束仍允许像素支持的陷波；交叉附近可增加锚点缩小身份歧义。
            emission += np.abs(observations[:, 0] - guide) / (bottom - top) * 20
        # 第一有效列没有前驱，初始代价由本列颜色证据决定。
        if previous is None:
            # 每条候选路径的累计代价，用于最终回溯。
            cost = emission
            # 记录到达当前候选的最小累计代价前驱。
            back = np.zeros(len(observations), int)
        # Codex说明(自动生成)： 处理前面条件都未命中时的默认分支。
        else:
            # 累加跨列垂直位移代价并封顶，允许像素支持的陡峭陷波。
            transitions = previous[0][None, :] + np.minimum(
                abs(observations[:, 0, None] - previous[1][None, :])
                / (bottom - top)
                * 20,
                8,
            )
            # 记录到达当前候选的最小累计代价前驱。
            back = transitions.argmin(axis=1)
            # 每条候选路径的累计代价，用于最终回溯。
            cost = transitions[np.arange(len(observations)), back] + emission
        # 保存最优前驱索引，使回溯不必重新计算转移矩阵。
        states.append(back)
        # 保留前一有效列的代价和像素行坐标。
        previous = (cost, observations[:, 0])
    # 反向回溯代价最低的候选路径；没有候选的列不伪造 observed 样本。
    selected = int(previous[0].argmin())
    # 收集选中的原图像素坐标，稍后反转为频率递增顺序。
    recovered = []
    # 与每个坐标同步收集颜色观测或人工辅助的来源标记。
    provenance = []
    # 从最低总代价末端反向找到完整候选序列。
    for (x, observations), back in zip(reversed(columns), reversed(states)):
        # 把图框局部坐标还原为原图坐标，便于叠加与审查。
        recovered.append((x + left, observations[selected, 0] + top))
        # 只要截面中心受放宽颜色影响，就披露人工辅助而非独立颜色观测。
        provenance.append(
            "manual_anchor"
            if x in anchor_map
            else "manual_guided" if observations[selected, 2] else "observed"
        )
        # 选择当前累计代价最低的候选索引。
        selected = int(back[selected])
    # 自动与人工选色路径共用二维尖端恢复；人工锚点是明确约束，不移动。
    from .raster_path_geometry import preserve_raster_turns

    recovered_points = np.asarray(recovered[::-1])
    protected = [index for index, (x, _y) in enumerate(recovered_points) if int(round(x - left)) in anchor_map]
    recovered_points = preserve_raster_turns(mask, recovered_points - (left, top), protected_indexes=protected) + (left, top)
    return recovered_points, tuple(provenance[::-1])


# 把像素修正结果转换为工作区共用的频率和幅度数据合同。
def edited_curves(
    rgb, box, specs, exclusions, *, start_hz, stop_hz, y_min_db, y_max_db, spacing
):
    # 延迟导入避免与原数字化入口循环依赖，保持同一返回数据合同。
    from .datasheet_digitizer import DigitizedCurve

    # 编辑器最多处理八条已由用户选择身份的目标线。
    if not isinstance(specs, list) or not 1 <= len(specs) <= 8:
        # Codex说明(自动生成)： 抛出 ValueError('人工路径需要 1–8 条已明确身份的曲线。')，明确提示输入、状态或处理流程无法继续。
        raise ValueError("人工路径需要 1–8 条已明确身份的曲线。")
    # 按用户选择顺序保存结果，身份 UUID 保留在修线方案中。
    curves = []
    # 检查身份唯一性，避免恢复方案把两条曲线绑定到同一个身份。
    ids = set()
    # 图框四边分别绑定频率与幅度校准端点。
    left, top, right, bottom = box
    # 每个目标身份独立追踪，交叉时由其自身锚点约束。
    for spec in specs:
        # 读取稳定身份；它与后续界面 A/B/C 显示序号分开。
        identity = str(spec.get("id", ""))
        # 空或重复身份不能建立可靠的保存恢复关系。
        if not identity or identity in ids:
            # Codex说明(自动生成)： 抛出 ValueError('人工曲线身份必须非空且唯一。')，明确提示输入、状态或处理流程无法继续。
            raise ValueError("人工曲线身份必须非空且唯一。")
        # 登记当前身份，供后续目标检查重复。
        ids.add(identity)
        # 像素坐标和证据类别共同进入频率幅度转换。
        points, provenance = trace_pixel_path(
            rgb, box, spec["rgb"], spec.get("anchors", []), exclusions
        )
        # 原图横坐标在有效图框中的比例，无量纲。
        fraction = (points[:, 0] - left) / (right - left)
        # 把原图水平像素位置映射到线性或对数频率，单位 Hz。
        frequency = (
            np.exp(np.log(start_hz) + fraction * (np.log(stop_hz) - np.log(start_hz)))
            if spacing == "log"
            else start_hz + fraction * (stop_hz - start_hz)
        )
        # 按校准上下边界把像素高度转换为带符号的幅度 dB。
        magnitude = y_max_db - (points[:, 1] - top) / (bottom - top) * (
            y_max_db - y_min_db
        )
        # 保留原始像素与证据；覆盖比例是启发式分数，不是识别概率。
        curves.append(
            DigitizedCurve(
                color=str(spec.get("label") or identity),
                rgb=tuple(spec["rgb"]),
                frequency_hz=frequency,
                magnitude_db=magnitude,
                pixel_points=points,
                confidence=min(1, len(points) / (right - left + 1)),
                observed_samples=provenance.count("observed"),
                sample_provenance=provenance,
            )
        )
    # 返回不可变的曲线集合给现有工作区与视觉复核流程。
    return tuple(curves)
