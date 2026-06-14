"""Feature mixins for the Parth TUI App.

Each mixin groups a cohesive cluster of ``ParthTUI`` behaviour (and its
instance state) into its own module so the main app class stays navigable.
Mixins are not standalone widgets — they assume ``self`` is the composed
``ParthTUI`` instance and rely on methods/attributes provided by it.
"""
