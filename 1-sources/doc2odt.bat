:: TODO path to soffice
:: can batch-convert when %1 = *.doc
:: python won't read it - probably expects different filter
soffice --headless --convert-to odt:writer8 %1
