
require(readxl)
require(dplyr)
require(readr)
#library(devtools)
#install_github("alxbetz/bendr")
require(bendr)
require(ggplot2)
require(argparser)
require(nlmrt)
require(nls2)
require(tidyr)
require(stringr)

p <- arg_parser("Calculate EC50, Ec10 and NTC")
p <- add_argument(p, "dir", help="output directory")
p <- add_argument(p, "file", help="number of decimal places")
argv <- parse_args(p)

print(argv)
fname = argv$file
outdir = argv$dir
print(fname)
print(outdir)

if(endsWith(fname,'xls') || endsWith(fname,'xlsx')) {
  edata = readxl::read_excel(fname)
} else if (endsWith(fname,'csv')){
  edata = read_csv2(fname)
}

drc.formula = effect ~ 100 / (1 + 10^((logEC50-logconc) * slope))
nrep = ncol(edata) - 1
names(edata) <- c('conc',paste0('rep', as.character(seq(nrep))))
edataf = edata %>% dplyr::filter(conc > 0)
if(nrep > 1) {
  ecol_idx = seq(2,nrep+1)
  fo = bendr::fitdr_replicates(drc.formula,edataf,ecol_idx,conc,debug=F)
} else {
  colnames(edataf) = c("conc","effect")
  edatafLog = edataf %>% dplyr::mutate(logconc = log10(conc))
  fo = bendr::fitdr(drc.formula,edatafLog)
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



bname = sub(pattern = "(.*)\\..*$", replacement = "\\1", basename(fname))
po = bendr::plot_single_drc(fo) +
  scale_x_continuous('log10 Concentration [mg/L]') +
  scale_y_continuous('% Cell Viability',breaks = seq(0,120,by=20), labels = as.character(seq(0,120,by=20)),limits = c(-5,120)) +
  geom_vline(xintercept = log10(fo$ec50),color="gray",lty =1,lwd = 1) +
  theme_bw()

print(file.path(outdir,paste0(bname,'.png')))
ggsave(filename = file.path(outdir,paste0(bname,'.png')),po,dpi=150,width = 6, height = 5)
saveRDS(object = fo,file = file.path(outdir,paste0(bname,'.RDS')))
write_csv(fo$plot.data,file.path(outdir,paste0(bname,"_plotdata.csv")))
write_csv(est_vals,file.path(outdir,paste0(bname,"_estimated.csv")))
