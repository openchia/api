from bisect import bisect_left


def take_closest(list_, number):
    pos = bisect_left(list_, number)
    if pos == 0:
        return [list_[0]]
    if pos == len(list_):
        return [list_[-1]]
    before = list_[pos - 1]
    after = list_[pos]
    if after - number == number - before:
        return [after, before]
    elif after - number < number - before:
        return [after]
    else:
        return [before]
