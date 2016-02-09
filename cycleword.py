BINARY = ['0', '1']


def _simplify_period(period):
    for i in range(1, len(period)):
        if len(period) % i != 0:
            continue
        else:
            extended = period[0:i] * (len(period)/i)
            if period == extended:
                return period[0:i]
    return period


def _simplify_initial(initial, period):
    while initial.endswith(period):
        initial = initial[0:-len(period)]
    return initial


class PeriodicBinary(object):
    initial = ''
    period = ''

    def _normalize_form(self):
        self.period = _simplify_period(self.period)
        self.initial = _simplify_initial(self.initial, self.period)

    def __init__(self, initial, period):
        if not isinstance(initial, str) or not isinstance(period, str):
            raise ValueError("Initial segment and period must be strings.")

        if len(period) == 0:
            raise ValueError("Period must be nonempty")

        if not all([c in BINARY for c in initial]) or not all([c in BINARY for c in period]):
            raise ValueError("Initial segment and period must be binary strings.")

        self.period = period
        self.initial = initial
        self._normalize_form()

    def __eq__(self, other):
        if not isinstance(other, PeriodicBinary):
            return False
        if self.initial == other.initial and self.period == other.period:
            return True
        elif len(self.initial) != len(other.initial) or len(self.initial) == 0:
            return False
        elif self.initial[0:-1] != other.initial[0:-1]:
            return False
        else:
            return self.initial[-1] == other.period and other.initial[-1] == self.period

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return "%s[:%s:]" % (self.initial, self.period)

    def __repr__(self):
        return str(self)

    def equal_in_s1(self, other):
        if not isinstance(other, PeriodicBinary):
            return False
        if self.initial == other.initial and self.period == other.period:
            return True
        elif len(self.initial) != len(other.initial):
            return False
        elif self.initial[0:-1] != other.initial[0:-1]:
            return False
        elif len(self.initial) == 0:
            return {self.period, other.period} == set(BINARY)
        else:
            return self.initial[-1] == other.period and other.initial[-1] == self.period

    def prepend(self, prefix):
        return PeriodicBinary(prefix + self.initial, self.period)
