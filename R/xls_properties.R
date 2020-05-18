require(tidyverse)
dat = readxl::read_xlsx('D:/polybox/dr_database/overview_files/Cells_Dose_ResponsesV15.xlsm',sheet = 'IDs')
colnames(dat) = make.names(colnames(dat))
str_extract(string = dat$Date,pattern = "\\d{4}")
as.Date(dat$Date,origin = "1899-12-30")

extract_year = Vectorize(function(x) {
  if(is.na(x)) {
    return(x)
  }
  
  if(!is.na(as.numeric(x)) && as.numeric(x) > 20000 ) {
    x = as.Date(as.numeric(x),origin = "1899-12-30")
    
  }
  str_extract(x,pattern = "\\d{4}")
})

extract_year(dat$Date)

colnames(dat)
dat$File.ID..AB
dat$File.ID..AB
year_info = dat %>% mutate(year = extract_year(Date)) %>% dplyr::select(
  year,
  File.ID..AB,
  File.ID.CFDA,
  File.ID.NR,
  File.ID.PB,
) %>% pivot_longer(cols = 2:5,names_to="endpoint",values_to = "ID") %>%
  unique() %>% mutate(endpoint = str_extract(endpoint,"AB|CFDA|NR|PB")) %>% drop_na()
write_csv(x = year_info,'D:/polybox/dr_database/celltox_test/data/year_info.csv')