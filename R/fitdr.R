
require(readxl)
require(dplyr)
require(readr)
#library(remotes)
#remotes::install_github("alxbetz/bendr")
require(bendr)
require(ggplot2)
require(argparser)
require(nlmrt)
require(nls2)
require(tidyr)
require(stringr)

p <- arg_parser("Calculate EC50, EC10 and NTC")
p <- add_argument(p, "dir", help="output directory")
p <- add_argument(p, "file", help="data file")
p <- add_argument(p, "ci_method", help="confidence interval calculation method ['bootstrap','delta']",default = "delta")
argv <- parse_args(p)

print(argv)
fname = argv$file
outdir = argv$dir
ci_method = argv$ci_method
print(fname)
print(outdir)

if(endsWith(fname,'xls') || endsWith(fname,'xlsx')) {
  edata = readxl::read_excel(fname)
} else if (endsWith(fname,'csv')){
  edata = read_csv(fname)
  #handle the case that semicolons are used as separators in csv
  if(ncol(edata) == 1) {
    edata = read_csv2(fname)
  }
}
bname = sub(pattern = "(.*)\\..*$", replacement = "\\1", basename(fname))
edata = edata[colSums(!is.na(edata)) > 0]
nrep = ncol(edata)-1
repnames= sapply(as.character(seq(nrep)),function(x) paste0("replicate",x))
colnames(edata) = c("conc",repnames)

if(ncol(edata) > 2) {
  edata_long = tidyr::pivot_longer(edata,2:ncol(edata),names_to = "replicateID",values_to = "effect")
} else {
  edata_long = edata %>% mutate(replicateID = 1) %>% rename(effect = replicate1)
}
edata_long = edata_long  %>% dplyr::filter(conc > 0) %>% mutate(logconc = log10(conc)) %>% drop_na()

q5 = quantile(edata_long$effect,0.05)
q95 = quantile(edata_long$effect,0.95)
qdiff = q95 - q5
if(qdiff < 50 ) {
  po = ggplot(edata_long) + geom_point(aes(x=logconc,y=effect)) +
    scale_x_continuous('log10 Concentration [mg/L]') +
    scale_y_continuous('% Cell Viability',breaks = seq(0,120,by=20), labels = as.character(seq(0,120,by=20)),limits = c(-5,120)) +
    theme_bw()
  edirection = NA
  evalue = NA
  if(q5 > 50) {
    edirection = "greater"
    evalue = max(edata_long$conc)
  } else if(q95 < 50) {
    edirection = "smaller"
    evalue = min(edata_long$conc)
  }


  est_vals = tibble(params = c("exceeds_direction","exceeds_value"),
                    values = c(edirection,evalue))


} else {


drc.formula = effect ~ 100 / (1 + 10^((logEC50-logconc) * slope))
edata = edata %>% select_if(~sum(!is.na(.)) > 0)

names(edata) <- c('conc',paste0('rep', as.character(seq(nrep))))
edataf = edata %>% dplyr::filter(conc > 0)
if(nrep > 1) {
  ecol_idx = seq(2,nrep+1)

  fo = bendr::fitdr_replicates(drc.formula,edataf,ecol_idx,conc,ci_method=ci_method)
} else {
  colnames(edataf) = c("conc","effect")
  edatafLog = edataf %>% dplyr::mutate(logconc = log10(conc))
  fo = bendr::fitdr(drc.formula,edatafLog,ci_method=ci_method)
  fo$nreplicates = 1
}

fo$ntc = tryCatch(findNTC(fo),
         error = function(c) NA
)

sum_idx = c(
  'ec50',
  'ec50.ci',
  'ec10',
  'ec10.ci',
  'slope',
  'slope.ci',
  'ntc',
  'confidence.level'
)
vals = unlist(fo[sum_idx])
parnames =  str_replace(names(vals),'ntc.logEC50','ntc')
est_vals = tibble(params = parnames,values=vals)



  po = bendr::plot_single_drc(fo) +
    scale_x_continuous('log10 Concentration [mg/L]') +
    scale_y_continuous('% Cell Viability',breaks = seq(0,120,by=20), labels = as.character(seq(0,120,by=20)),limits = c(-5,120)) +
    geom_vline(xintercept = log10(fo$ec50),color="gray",lty =1,lwd = 1) +
    theme_bw()

  write_csv(fo$plot.data,file.path(outdir,paste0(bname,"_plotdata.csv")))
  saveRDS(object = fo,file = file.path(outdir,paste0(bname,'.RDS')))
}

write_csv(est_vals,file.path(outdir,paste0(bname,"_estimated.csv")))

print(file.path(outdir,paste0(bname,'.png')))
ggsave(filename = file.path(outdir,paste0(bname,'.png')),po,dpi=150,width = 6, height = 5)

