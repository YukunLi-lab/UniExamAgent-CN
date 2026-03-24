"""
OCR 公式纠错模块
自动修复 OCR 识别错位、拆分、乱码的数学公式
"""

import re
from typing import Dict, List, Tuple


class OCRFormulaCorrector:
    """OCR 数学公式纠错器"""

    # OCR 常见符号错误映射（Unicode 乱码 → 正确符号）
    SYMBOL_MAP = {
        '∂': r'\partial',      # 偏导符号
        'ρ': r'\rho',          # 密度
        'ω': r'\omega',        # 角频率
        '∫': r'\int',          # 积分
        'Σ': r'\Sigma',        # 求和
        'Δ': r'\Delta',        # 增量
        'θ': r'\theta',        # 角度
        'φ': r'\phi',          # 相位
        'λ': r'\lambda',       # 波长
        'μ': r'\mu',           # 系数
        'ε': r'\epsilon',     #  epsilon
        'σ': r'\sigma',       # 标准差
        'α': r'\alpha',        # alpha
        'β': r'\beta',         # beta
        'γ': r'\gamma',        # gamma
        'η': r'\eta',          # eta
        'τ': r'\tau',          # tau
        'π': r'\pi',          # 圆周率
        '∞': r'\infty',       # 无穷
        '·': r'\cdot',        # 点乘
        '×': r'\times',       # 乘号
        '÷': r'\div',         # 除号
        '≤': r'\leq',         # 小于等于
        '≥': r'\geq',         # 大于等于
        '≠': r'\neq',         # 不等于
        '±': r'\pm',          # 正负
    }

    # 三角函数（空格拆分的）
    TRIG_FUNCTIONS = {
        'sin': r'\sin',
        'cos': r'\cos',
        'tan': r'\tan',
        'cot': r'\cot',
        'sec': r'\sec',
        'csc': r'\csc',
    }

    # 反三角函数
    INV_TRIG_FUNCTIONS = {
        'arcsin': r'\arcsin',
        'arccos': r'\arccos',
        'arctan': r'\arctan',
    }

    # 已知的物理公式结构（用于纠错）
    FORMULA_PATTERNS: List[Dict] = [
        # 波速公式 u = sqrt(Y/rho)
        {
            'pattern': r'u\s*=\s*Y\s*ρ?\s*',
            'correct': r'u = \sqrt{\frac{Y}{\rho}}',
            'context': 'wave_velocity'
        },
        # 动能公式 dE_k = 1/2 dm v^2
        {
            'pattern': r'dE_k\s*=\s*1\s*/?\s*2?\s*dm\s*v\s*\^?\s*2',
            'correct': r'dE_k = \frac{1}{2}dm v^2',
        },
        # 质能关系 E = mc^2
        {
            'pattern': r'E\s*=\s*m\s*c\s*\^?\s*2',
            'correct': r'E = mc^2',
        },
        # 动能 E_k = 1/2 mv^2
        {
            'pattern': r'E_k\s*=\s*1\s*/?\s*2?\s*m\s*v\s*\^?\s*2',
            'correct': r'E_k = \frac{1}{2}mv^2',
        },
    ]

    def __init__(self):
        self._init_patterns()

    def _init_patterns(self):
        """初始化编译的正则表达式"""
        # 构建三角函数空格拆分模式: s i n → \sin
        trig_pattern_parts = []
        for trig in self.TRIG_FUNCTIONS:
            parts = list(trig)
            # 匹配被空格拆分的单个字母，如 s i n
            spaced = r'\s+'.join(parts)
            trig_pattern_parts.append(f'(?:{trig}|{spaced})')

        # 匹配独立的单个字母（可能是变量）
        self._single_letter_var = re.compile(
            r'(?<![a-zA-Z])([a-zA-Z])\s+([a-zA-Z])?(?![a-zA-Z])'
        )

        # 匹配上标数字（空格拆分）: v 2 → v^2
        self._superscript_num = re.compile(
            r'([a-zA-Z])\s+(\d+)'
        )

        # 匹配分数（空格拆分）: 1 2 → \frac{1}{2}
        self._fraction = re.compile(
            r'(?<!\w)(\d+)\s+/\s+(\d+)(?!\w)|'
            r'(?<!\w)(\d+)\s+(\d+)(?=\s*[\u4e00-\u9fff]|$)(?!\w)'
        )

        # 匹配行尾的换行公式片段（如被换行拆分的公式）
        self._line_break_formula = re.compile(
            r'([a-zA-Z0-9\^\-\+]+)\s*[\n\r]+\s*([a-zA-Z0-9\^\-\+])'
        )

    def correct(self, text: str) -> str:
        """
        对 OCR 文本进行公式纠错

        Args:
            text: OCR 识别的原始文本

        Returns:
            纠错后的文本
        """
        if not text:
            return text

        # 1. 修复乱码符号
        text = self._fix_symbols(text)

        # 2. 修复空格拆分的三角函数
        text = self._fix_trig_functions(text)

        # 3. 修复空格拆分的上标（如 v 2 → v^2）
        text = self._fix_superscripts(text)

        # 4. 修复空格拆分的变量（如 d E_k → dE_k）
        text = self._fix_split_variables(text)

        # 5. 修复分数表达式
        text = self._fix_fractions(text)

        # 6. 修复换行拆分的公式
        text = self._fix_line_break_formulas(text)

        # 7. 应用已知公式模式
        text = self._apply_formula_patterns(text)

        # 8. 清理多余的空格
        text = self._cleanup_spaces(text)

        return text

    def _fix_symbols(self, text: str) -> str:
        """修复乱码符号"""
        for wrong, correct in self.SYMBOL_MAP.items():
            text = text.replace(wrong, correct)
        # 修复希腊字母与变量粘连的问题（如 \partialy → \partial y）
        greek_cmds = [r'\partial', r'\rho', r'\omega', r'\sigma', r'\lambda', r'\alpha', r'\beta', r'\gamma', r'\eta', r'\tau']
        for cmd in greek_cmds:
            # 在希腊字母命令和后面的变量之间加空格
            text = re.sub(rf'({re.escape(cmd)})([a-zA-Z])', rf'\1 \2', text)
        return text

    def _fix_trig_functions(self, text: str) -> str:
        """修复空格拆分的三角函数"""
        all_trig = {**self.TRIG_FUNCTIONS, **self.INV_TRIG_FUNCTIONS}
        for trig, replacement in all_trig.items():
            # 匹配被空格拆分的单个字母，如 s i n
            spaced = r'\s+'.join(list(trig))
            pattern = re.compile(rf'\b({re.escape(trig)}|{spaced})\b', re.IGNORECASE)
            # 使用 lambda 避免 re.sub 对替换字符串的错误解析
            text = pattern.sub(lambda m: replacement, text)
        return text

    def _fix_superscripts(self, text: str) -> str:
        """修复上标数字（v 2 → v^2）"""
        def replace_superscript(m):
            var = m.group(1)
            num = m.group(2)
            # 检查是否是已知的上标表达式
            return f'{var}^{num}'

        # 匹配 "变量 数字" 或 "变量 数字"
        pattern = re.compile(r'([a-zA-Z])\s+(\d+)(?!\s*[/\d])')
        text = pattern.sub(replace_superscript, text)

        # 特殊物理量上标
        special_superscripts = [
            (r'\bv\s*2\b', 'v^2'),
            (r'\bu\s*2\b', 'u^2'),
            (r'\bA\s*2\b', 'A^2'),
            (r'\\omega\s*2\b', r'\omega^2'),
            (r'\bE\s*2\b', 'E^2'),
            (r'\bm\s*2\b', 'm^2'),
        ]
        for pattern, replacement in special_superscripts:
            text = re.sub(pattern, lambda m: replacement, text)

        return text

    def _fix_split_variables(self, text: str) -> str:
        """修复空格拆分的变量名（d E_k → dE_k，d E k → dE_k）"""
        # 首先修复 E_k 类型的模式（单个大写字母 + 下标）
        text = re.sub(r'\b([A-Z])\s*_\s*([a-zA-Z\d])', r'\1_\2', text)

        # 修复连续空格拆分的变量（d E k → dE_k）
        # 只处理类似 "X Y_z" 的模式，其中 Y 是大写字母（表示下标变量）
        # d E k → dE_k (E是大写，k是小写 → E_k)
        # d m v → dm v (m, v都是小写，不需要合并)
        text = re.sub(r'\b([a-z])\s+([A-Z])\s+([a-z])\b',
                       lambda m: m.group(1) + m.group(2) + '_' + m.group(3), text)

        # 修复两个字母被空格分开（d E → dE），不在 LaTeX 命令内部
        pattern = re.compile(r'(?<!\\)\b([a-zA-Z])\s+([a-zA-Z](?:_[a-zA-Z\d])?)\b')
        text = pattern.sub(lambda m: m.group(1) + m.group(2), text)

        return text

        return text

    def _fix_fractions(self, text: str) -> str:
        """修复分数表达式"""
        # 匹配 1/2, 1 2 等形式
        # 使用 lambda 避免转义问题
        text = re.sub(r'(\d+)\s*/\s*(\d+)', lambda m: r'\frac{' + m.group(1) + r'}{' + m.group(2) + r'}', text)
        text = re.sub(r'1\s+2(?=\s|$|,)', lambda m: r'\frac{1}{2}', text)
        return text

    def _fix_line_break_formulas(self, text: str) -> str:
        """修复换行拆分的公式"""
        # 匹配行尾的不完整公式片段
        lines = text.split('\n')
        corrected_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # 检查是否是公式行的结尾（以运算符或变量结尾）
            if re.search(r'[a-zA-Z0-9\^\_\+\-]\s*$', line) and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                # 如果下一行是变量开头（可能是公式继续）
                if re.match(r'^[a-zA-Z0-9\^\_\+\-]', next_line) and len(next_line) < 20:
                    # 合并两行
                    line = line.rstrip() + ' ' + next_line
                    i += 1  # 跳过下一行

            corrected_lines.append(line)
            i += 1

        return '\n'.join(corrected_lines)

    def _apply_formula_patterns(self, text: str) -> str:
        """应用已知公式模式进行纠错"""
        # 波速公式
        text = re.sub(
            r'u\s*=\s*Y\s*\\?rho?',
            lambda m: r'u = \sqrt{\frac{Y}{\rho}}',
            text
        )

        # 能量密度公式
        text = re.sub(
            r'w\s*=\s*\\?rho?\s*A\s*\^?\s*2?\s*\\?omega?\s*\^?\s*2?',
            lambda m: r'w = \rho A^2 \omega^2',
            text
        )

        # 波强公式
        text = re.sub(
            r'I\s*=\s*1\s*/?\s*2?\s*\\?rho?\s*A\s*\^?\s*2?\s*\\?omega?\s*\^?\s*2?\s*u',
            lambda m: r'I = \frac{1}{2}\rho A^2 \omega^2 u',
            text
        )

        return text

    def _cleanup_spaces(self, text: str) -> str:
        """清理多余的空格"""
        # 公式内多余空格（只在特殊符号周围，使用普通空格而非所有空白符）
        text = re.sub(r' *([\^\_\{\}]) *', r'\1', text)
        # 修复 \frac{1}{2} 周围多余空格（只在 \frac 后面）
        text = re.sub(r'\\frac *', r'\\frac', text)
        text = re.sub(r'\\sqrt *', r'\\sqrt', text)

        # 中文与公式间的空格
        text = re.sub(r' *\$+ *', '$', text)

        return text

    def wrap_formulas(self, text: str) -> str:
        """
        将公式包裹为 LaTeX 格式

        Args:
            text: 已纠错的文本

        Returns:
            包裹 LaTeX 公式后的文本
        """
        # 如果文本中已经包含 LaTeX 命令（\开头的），直接返回不包裹
        # 因为 OCR 纠错后的公式已经包含正确的 LaTeX
        if '\\' in text:
            return text

        # 使用 lambda 避免转义问题
        # 匹配包含 = 的等式公式
        text = re.sub(
            r'(?<!\$)([a-zA-Z_]\w*\s*=\s*[a-zA-Z_\d\s\^\+\-]+)(?!\$)',
            lambda m: '$' + m.group(1) + '$',
            text
        )
        # 匹配单独的希腊字母表达式
        text = re.sub(
            r'(?<!\$)([\\][a-zA-Z]+\s*[a-zA-Z\d]?)',
            lambda m: '$' + m.group(1) + '$',
            text
        )
        return text


def correct_ocr_formulas(text: str, wrap: bool = True) -> str:
    """
    OCR 公式纠错主函数

    Args:
        text: OCR 识别的原始文本
        wrap: 是否自动包裹公式为 LaTeX 格式

    Returns:
        纠错并格式化后的文本
    """
    corrector = OCRFormulaCorrector()
    corrected = corrector.correct(text)

    if wrap:
        corrected = corrector.wrap_formulas(corrected)

    return corrected


# 单元测试
if __name__ == "__main__":
    test_text = """
    动能 d E k = 1 2 d m v 2

    波速 u = Y ρ

    w = ρ A 2 ω 2 s i n 2( t − x / u )

    ∂ y / ∂ t = − A s i n ( ω t − x / u ) ω
    """

    result = correct_ocr_formulas(test_text)
    print("Original:")
    print(test_text)
    print("\nCorrected:")
    print(result)
