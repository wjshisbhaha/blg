"""HUD批量测试配置。

每项格式：("配置文件名", ["测试命令1", "测试命令2"])
配置文件名可以带或不带 .ini 后缀。
"""

# t24执行后，HUD软件生成Sparkle.jpg的默认目录。
# Windows路径请使用r前缀，例如：r"D:\HUD\pic"
SPARKLE_SOURCE_DIR = None

# 每次测试后，将Sparkle.jpg以唯一文件名复制到这个目录。
# 例如：r"D:\HUD测试结果\图片"
SPARKLE_SAVE_DIR = None

# 可选亮度文件；配置后程序会在测试前发送：ssf-完整路径
# 例如：r"D:\test\test.bin"
BRIGHTNESS_FILE = None

TEST_PLAN = [
    ("11", ["t24", r"ssf-D:\test\test.bin", "t6"]),
    ("22", ["t24", "t6"]),
    ("33", ["t24", "t6"]),
    ("44", ["t24", "t6"]),
]
