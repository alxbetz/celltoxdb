require(tidyverse)
dat = readxl::read_excel('~/polybox2/dr_database/Cells_Dose_ResponsesV17.xlsm',sheet = 'IDs')

selCol = function(x) stringr::str_detect(x,'CAS|Chemical|Experimental|Estimated|g/mol')


cdat = dat[,selCol(colnames(dat))] %>% unique()
colnames(cdat)
#cdat %>% mutate_
colnames(cdat) = make.names(colnames(cdat)) %>% str_to_lower() %>% str_remove_all(.,"..in.atm.m.3.mole.|..in.mg.l.|\\.$") %>%
  str_remove(.,'\\.water')


getIndexValue = Vectorize(function(pred,exp,exp_uc) {
  if(!is.na(exp_uc)) { return(exp_uc) }
  if(!is.na(exp)) { return(exp) }
  else { pred }
})

cdatf = cdat %>%
  mutate_at(c('estimated.henry.constant','g.mol','user.corrected.g.mol'),as.double) %>%
  mutate(index.log.kow = getIndexValue(estimated.log.kow,experimental.log.kow,user.corrected.experimental.log.kow)) %>%
  mutate(index.solubility = getIndexValue(estimated.solubility,experimental.solubility,user.corrected.experimental.solubility)) %>%
  mutate(index.henry.constant = getIndexValue(estimated.henry.constant,experimental.henry.constant,user.corrected.experimental.henry.constant)) %>%
  mutate(molecular_weight = getIndexValue(NA,g.mol,user.corrected.g.mol)) %>%
  dplyr::select(-g.mol,-user.corrected.g.mol)


colnames(cdatf) = str_replace_all(colnames(cdatf),'\\.','_')
cdatf = cdatf %>% rename(name = chemical, cas_number = cas_nr)
require(jsonlite)

write_file(jsonlite::toJSON(cdatf,dataframe = 'rows',digits=9),path = '~/polybox2/dr_database/celltox_test/data/chemicals_info.json')

jsonlite::toJSON(cdatf %>% mutate_if(is.double,function(x) round(x,5)),dataframe = 'rows',digits=5,pretty=T)
