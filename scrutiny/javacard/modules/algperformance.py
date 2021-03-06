from typing import Dict, List, Optional

from dominate import tags
from overrides import overrides

from scrutiny.htmlutils import show_hide_div, table
from scrutiny.interfaces import ContrastModule, ContrastState
from scrutiny.javacard.modules.jcalgtest import JCAlgTestModule,\
    PerformanceResult


class AlgPerformance(JCAlgTestModule):
    """Scrutiny algorithm performance module"""

    def __init__(self, module_name="Algorithm Performance"):
        super().__init__(module_name)
        self.performance: Dict[str, PerformanceResult] = {}

    @overrides
    def contrast(self, other):
        super().contrast(other)

        matching = {}
        erroneous = {}
        missing = {}
        mismatch = {}
        skipped = {}

        for key in self.performance:

            if key not in other.performance.keys():
                missing[key] = [self.performance[key], None]
                continue

            ref: PerformanceResult = self.performance[key]
            prof: PerformanceResult = other.performance[key]

            if ref.error != prof.error:
                erroneous[key] = [ref, prof]
                continue

            if ref.error:
                matching[key] = [ref, prof]
                continue

            # if ref.operation_avg() <= 2 * ref.baseline_avg():
            #     skipped[key] = [ref, prof]
            #     continue

            avg_diff = abs(ref.operation_avg() - prof.operation_avg())
            if avg_diff > ref.operation_max() - ref.operation_min():
                mismatch[key] = [ref, prof]
                continue

            matching[key] = [ref, prof]

        for key in other.performance.keys():
            if key not in self.performance.keys():
                missing[key] = [None, other.performance[key]]

        contrast_module = AlgPerformanceContrast()
        contrast_module.matching = matching
        contrast_module.erroneous = erroneous
        contrast_module.missing = missing
        contrast_module.mismatch = mismatch
        contrast_module.skipped = skipped

        return [contrast_module]

    @overrides
    def add_result(self, key: str, result: PerformanceResult) -> None:
        self.performance[key] = result


class AlgPerformanceContrast(ContrastModule):
    """Scrutiny algorithm performance contrast module"""

    def __init__(self, module_name="Algorithm Performance"):
        super().__init__(module_name)
        self.matching: Dict[str, List[PerformanceResult]] = {}
        self.erroneous: Dict[str, List[PerformanceResult]] = {}
        self.missing: Dict[str, List[Optional[PerformanceResult]]] = {}
        self.mismatch: Dict[str, List[PerformanceResult]] = {}
        self.skipped: Dict[str, List[PerformanceResult]] = {}

    @overrides
    def get_state(self):
        if self.mismatch or self.erroneous:
            return ContrastState.SUSPICIOUS
        if self.missing:
            return ContrastState.WARN
        return ContrastState.MATCH

    @overrides
    def project_html(self, ref_name: str, prof_name: str) -> None:
        self.output_intro()

        if self.missing:
            self.output_missing(ref_name, prof_name)

        self.output_matching()

    def output_intro(self):
        """Output introductory section"""

        tags.h3("Algorithm Performance comparison results")
        tags.p("This module compares Java Card "
               "algorithm performance between the cards.")
        tags.h4("Overview:")
        tags.p(
            "The cards' performance match in " +
            str(len(self.matching)) + " algorithms."
        )
        tags.p(
            "There are " + str(len(self.missing)) +
            " algorithms with missing results for either card."
        )
        tags.p(
            "There are " + str(len(self.mismatch)) +
            " algorithms with different results."
        )
        tags.p(
            "There are " + str(len(self.erroneous)) +
            " algorithms that failed with different error message."
        )
        tags.p(
            str(len(self.skipped)) +
            " algorithms were omitted due to being too fast in general."
        )

    def output_missing(self, ref_name, prof_name):
        """Output missing measurements section"""

        tags.h4("Missing measurements in algorithm performance:",
                style="color:var(--yellow-color);display:inline-block")

        header = ["Algorithm",
                  ref_name + " (reference)",
                  prof_name + " (profiled)"]

        data = []
        for key in self.missing:
            ref = self.missing[key][0]
            prof = self.missing[key][1]

            reftext = "Failed"
            proftext = "Failed"

            if not ref:
                reftext = "Result missing"
            elif not ref.error:
                reftext = "{:.2f}".format(ref.operation_avg()) + " ms"

            if not prof:
                proftext = "Result missing"
            elif not prof.error:
                proftext = "{:.2f}".format(prof.operation_avg()) + " ms"

            data.append([key, reftext, proftext])

        sm_div = show_hide_div("performance_missing_div", hide=True)

        with sm_div:
            tags.p(
                "These are the algorithms which had their results missing on "
                "one of the cards. These should be checked manually."
            )
            table(data, header,
                  green_value="ms",
                  red_value="Failed")

    def output_matching(self):
        """Output matching section"""

        tags.h4("List of algorithms with matching results:",
                style="color:var(--green-color);display:inline-block")

        data = [[key] for key in self.matching]

        sm_div = show_hide_div("performance_matching_div", hide=True)

        with sm_div:
            tags.p(
                "These are the algorithms in which the cards performed "
                "similarly, or on which they failed with the same error."
            )
            table(data)
