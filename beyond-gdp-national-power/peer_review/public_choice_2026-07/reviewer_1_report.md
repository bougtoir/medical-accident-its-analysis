# Referee Report: Network Exclusion and State Collapse: From Maritime Isolation to Technological Access Denial in the Long Run of History

I read this paper with great interest. This is a fascinating research question, and it would be a great fit for Public Choice. Yet, I believe this version of the paper is not ready for publication, for the reasons I describe below.

## 1. Introduction and motivation

While reading the introduction, the first page does a good job setting the stage and motivating the question, but once it progresses, I felt lost about what was actually being done or why the choices made were important. For instance, on page 3, it jumps rather quickly to the contributions and provides little insight about why the classification between stock- and flow-oriented is relevant for the research question, which is not immediately intuitive for the reader. It also provides no information about how the classification was done, the sources used, and so on, leaving the reader unconvinced about the overall analytical framework.

## 2. Literature review

Similarly, the paper provides no literature review, which I think would be crucial for a paper like this. In doing so, it ends up omitting key contributions that would directly relate to this paper, especially from a public choice perspective. Piano (2019) and Boettke and Candela (2020), both published in this journal, directly discussed state capacity from a public choice perspective. Still in the public choice tradition, Hendrickson et al. (2018) and Geloso and Salter (2020) discuss many of the same issues here (see also Piano and Salter, 2021). It also misses other discussions and datasets that could provide important controls. On technological transfer, I would suggest Bologna Pavlik and Young (2019), which tests Diamond's (1997) hypothesis of technological transfer from East-West vs. North-South (see also Olsson and Hibbs, 2005). Likewise, Flückiger et al. (2022) use connectivity to Roman roads to measure economic integration. Fernández-Villaverde et al. (2023) directly speaks to the survival of polities given by their geographical location – to see the connection, the author even uses a "geographical barrier index", without citing a source or explaining how exactly it was constructed. Young (2016), Bastos (2025) and Rodriguez and Imam (2025), also published in this journal, could be useful on the margin.

## 3. Classification and data construction

While the author does provide the full classification in the Appendix, it does not provide any information on how the classification was actually done, or the sources it consulted (other than mentioning the source for 96 historical polities from "standard reference works"). Related to point 2, and although the author does cite Comin et al. (2010), it does not discuss at all their data on technology adoption, which is also the data used in Bologna Pavlik and Young (2019). Without motivating the choice of relevant variables or comparing it to previous benchmarks, the reader is pretty much lost and unconvinced about the construction of the data. I also missed a summary stats table, or maps showing the polities, which leaves the reader without much context on where these polities are located or the distribution of the sample across eras.

## 4. Methods

Again, when one reaches the methods section, the author provides only a list of the methods used, without discussing why they are appropriate, their identification assumptions, or why the reader should believe they are met. For instance, on the 2SLS section, the author says that "We instrument the closure indicator with the geographic barrier index, which captures natural defensibility (mountains, deserts, island geography) and plausibly affects state survival only through its influence on network accessibility, conditional on external threat, technological position, institutional quality, and era (Angrist et al. 1996)" but there are basically no arguments for why this is the case. In the results section, there is no first-stage regression, although an F-test is reported in the main text. More broadly, I think that given the small sample size and the extensive temporal coverage of the analysis, finding an appropriate instrument will be quite hard, and IV analysis will likely be underpowered. In turn, the author discussed that PSM improves balance, but we don't have any test of actual covariate balance. I'm not completely sure matching will be the best option overall, but on the margin, given the small number of observations and coarse covariates (most of them seem to be discrete indicators), something like coarse exact matching would be more fruitful.

## 5. Randomization inference and standard errors

Having said all this, I do believe that using randomization inference was an appropriate choice given the small sample size, and I appreciate the author's attention to this matter. The choice of appropriate errors will have a large impact on the results of this paper, and I think that spatial correlation will play a large role. I suggest Conley and Kelly (2025) as a good reference for it. Given the similar empirical setting, Appendix C of Bastos (2025), published in this journal (see here) could be a useful reference, as it accounts for outliers using effective regression weights (as in Aronow and Samii, 2026), tests for omitted variable bias (as in Masten and Poirier, 2026), and the aforementioned Conley standard errors.

## References

- Aronow, P. M. and Samii, C. (2016). Does regression produce representative estimates of causal effects? *American Journal of Political Science*, 60(1):250–267.
- Bastos, J. P. (2025). Colonial rule and economic freedom. *Public Choice*, 205(1), 79-104.
- Bologna Pavlik, J., & Young, A. T. (2019). Did technology transfer more rapidly East–West than North–South?. *European Economic Review*, 119, 216-235.
- Boettke, P.J., Candela, R.A. (2020). Productive specialization, peaceful cooperation, and the problem of the predatory state: lessons from comparative historical political economy. *Public Choice* 182, 331–352.
- Comin, D., Easterly, W., & Gong, E. (2010). Was the wealth of nations determined in 1000 BC?. *American Economic Journal: Macroeconomics*, 2(3), 65-97.
- Conley, T. G., & Kelly, M. (2025). The standard errors of persistence. *Journal of International Economics*, 153, 104027.
- Fernández-Villaverde, J., Koyama, M., Lin, Y., & Sng, T. H. (2023). The fractured-land hypothesis. *The Quarterly Journal of Economics*, 138(2), 1173-1231.
- Flückiger, M., Hornung, E., Larch, M., Ludwig, M., & Mees, A. (2022). Roman transport network connectivity and economic integration. *The Review of Economic Studies*, 89(2), 774-810.
- Geloso, V. J., & Salter, A. W. (2020). State capacity and economic development: Causal mechanism or correlative filter?. *Journal of Economic Behavior & Organization*, 170, 372-385.
- Hendrickson, J. R., Salter, A. W., & Albrecht, B. C. (2018). Preventing plunder: Military technology, capital accumulation, and economic growth. *Journal of Macroeconomics*, 58, 154-173.
- Olsson, O., & Hibbs Jr, D. A. (2005). Biogeography and long-run economic development. *European Economic Review*, 49(4), 909-938.
- Piano, E. E. (2019). State capacity and public choice: a critical survey. *Public Choice*, 178(1), 289-309.
- Piano, E. E., & Salter, A. W. (2021). The fundamental Coase of development: property rights foundations of the effective state. *Journal of Institutional Economics*, 17(1), 37-52.
- Masten, M. A., & Poirier, A. (2026). The effect of omitted variables on the sign of regression coefficients. *American Economic Review* (Forthcoming)
- Rodríguez, F., & Imam, P. (2025). Political growth collapses. *Public Choice*, 205(1), 183-217
- Young, A. T. (2016). What does it take for a roving bandit settle down? Theory and an illustrative history of the Visigoths. *Public Choice*, 168(1), 75-102.
