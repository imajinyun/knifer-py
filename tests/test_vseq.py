from kniferpy import vseq


def test_sequence_basics() -> None:
    assert not vseq.is_empty([1])
    assert vseq.contains([1, 2], 2)
    assert vseq.index_of([1, 2], 3) == -1
    assert vseq.reverse([1, 2, 3]) == [3, 2, 1]
    assert vseq.distinct([1, 1, 2, 3, 2]) == [1, 2, 3]


def test_transform_and_grouping() -> None:
    values = [1, 2, 3, 4]

    assert vseq.map_values(values, lambda item: item * 2) == [2, 4, 6, 8]
    assert vseq.filter_values(values, lambda item: item % 2 == 0) == [2, 4]
    assert vseq.reject(values, lambda item: item % 2 == 0) == [1, 3]
    assert vseq.find(values, lambda item: item > 2) == 3
    assert vseq.group_by(values, lambda item: item % 2) == {1: [1, 3], 0: [2, 4]}
    assert vseq.count_by(values, lambda item: item % 2) == {1: 2, 0: 2}


def test_chunk_window_flatten_page() -> None:
    assert vseq.chunk([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
    assert vseq.window([1, 2, 3], 2) == [[1, 2], [2, 3]]
    assert vseq.flatten([[1, 2], [3]]) == [1, 2, 3]
    assert vseq.page([1, 2, 3, 4, 5], 2, 2) == [3, 4]
