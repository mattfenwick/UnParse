from .combinators import parserFactory, itemBasic, itemPosition



Parser = parserFactory(itemBasic)

CountParser = parserFactory(itemPosition)
