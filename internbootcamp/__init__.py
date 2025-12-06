# internbootcamp package
__version__ = "2.0.0"

# Avoid importing all bootcamps (some pull heavy/optional deps like torch distributed).
# Downstream code should import specific bootcamps explicitly when needed.
