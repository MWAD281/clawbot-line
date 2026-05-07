class SelfDistiller:
    """
    Strong policies teach weaker ones
    """

    def distill(self, teacher, student, strength=0.2):
        for regime in student.genome:
            for k in student.genome[regime]:
                student.genome[regime][k] += (
                    teacher.genome[regime][k] - student.genome[regime][k]
                ) * strength
