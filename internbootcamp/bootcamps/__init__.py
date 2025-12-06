import pkgutil
import importlib


__all__ = []

# 自动导入子模块 + 提升 __all__ 中的内容
for importer, modname, ispkg in pkgutil.iter_modules(__path__, __name__ + "."):
    if ispkg:
        # NP_MM 依赖 torch 分布式，CPU 环境/裁剪环境可能触发崩溃；评测 Futoshiki 时直接跳过
        if modname.endswith(".NP_MM"):
            continue
        try:
            module = importlib.import_module(modname)
            module_name = modname.split(".")[-1]
            globals()[module_name] = module
            __all__.append(module_name)

            # 自动提升子模块中 __all__ 定义的符号
            if hasattr(module, '__all__'):
                for name in module.__all__:
                    if hasattr(module, name):
                        attr = getattr(module, name)
                        globals()[name] = attr
                        __all__.append(name)
        except Exception as e:
            # 使用宽泛异常以避免因可选依赖（如 torch/verl）缺失导致整个包导入失败
            print(f"[Warning] Failed to import {modname}: {e}")
