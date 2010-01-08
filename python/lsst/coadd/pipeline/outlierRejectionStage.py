from lsst.pex.logging import Log
import lsst.afw.image as afwImage
import lsst.afw.math as afwMath
import lsst.coadd.utils as coaddUtils
import baseStage

class OutlierRejectionStageParallel(baseStage.ParallelStage):
    """
    Pipeline stage to combine a list of masked images computing an outlier-rejected mean.
    
    Inputs must include:
    - mask of acceptable mask plane bits
    - some kind of criteria for how to compute "what is an outlier" including:
      - # of sigma
      - # of outlier iterations
      - use std dev or quartiles? (else always quartiles)
      - use mean or median? (else always median)
    - weight vector (a std::vector of doubles); I'd like this to be optional
        so if length = 0 then create a vector of 1.0 else require length to be correct
    """
    packageName = "coadd_pipeline"
    policyDictionaryName = "outlierRejectionStage_dict.paf"
    def process(self, clipboard):
        """Reject outliers"""
#         print "***** process ******"
#         print "clipboard keys:"
#         for key in clipboard.getKeys():
#             print "*", key

        maskedImageList = self.getFromClipboard(clipboard, "maskedImageList")
        print "maskedImageList =", maskedImageList
        weightList = self.getFromClipboard(clipboard, "weightList", doRaise=False)
        outlierRejectionPolicy = self.policy.get("outlierRejectionPolicy")
        
        allowedMaskPlanes = outlierRejectionPolicy.get("allowedMaskPlanes")
        badPixelMask = coaddUtils.makeBitMask(allowedMaskPlanes.split(), doInvert=True)

        statsControl = afwMath.StatisticsControl()
        statsControl.setNumSigmaClip(outlierRejectionPolicy.get("numSigma"))
        statsControl.setNumIter(outlierRejectionPolicy.get("numIterations"))
        statsControl.setAndMask(badPixelMask)
        statsControl.setNanSafe(False) # we're using masked images, so no need for NaN detection
        statsControl.setWeighted(True)
        
        if weightList != None:
            coadd = afwMath.statisticsStack(maskedImageList, afwMath.MEANCLIP, statsControl, weightList)
        else:
            coadd = afwMath.statisticsStack(maskedImageList, afwMath.MEANCLIP, statsControl)

        self.addToClipboard(clipboard, "coadd", coadd)

# this is (unfortunately) required by SimpleStageTester; but not by the regular middleware
class OutlierRejectionStage(baseStage.Stage):
    parallelClass = OutlierRejectionStageParallel
