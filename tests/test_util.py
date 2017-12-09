import pytest

from util import UserError, Logger, merge_into, merge


def test_new_usererror():
    msg = f"hello!"
    e: UserError = UserError(msg)
    assert e.message == msg


@pytest.mark.parametrize("header", ["test header", None])
@pytest.mark.parametrize("indent_amount", [0, 2, 4])
@pytest.mark.parametrize("spacious", [True, False])
@pytest.mark.parametrize("content", ["some-line", None])
def test_logger_header(capsys, header: str, indent_amount: int, spacious: bool, content: str):
    with Logger(header=header, indent_amount=indent_amount, spacious=spacious) as logger:
        if content is not None:
            logger.info(content)

    expected = ''
    expected = expected + (f'{header}\n' if header is not None else '')
    expected = expected + (f'\n' if header is not None and spacious else '')
    expected = expected + (f'{" " * indent_amount}{content}\n' if content else '')
    expected = expected + (f'{" " * indent_amount}\n' if spacious else '')
    assert capsys.readouterr().out == expected


@pytest.mark.parametrize("header", ["test header", None])
@pytest.mark.parametrize("indent_amount", [0, 2, 4])
@pytest.mark.parametrize("spacious", [True, False])
@pytest.mark.parametrize("content1", ["part1", None])
@pytest.mark.parametrize("content2", ["part2", None])
def test_logger_partial_line(capsys, header: str, indent_amount: int, spacious: bool, content1: str, content2: str):
    with Logger(header=header, indent_amount=indent_amount, spacious=spacious) as logger:
        if content1 is not None:
            logger.info(content1, newline=False)
        if content2 is not None:
            logger.info(content2, newline=True)

    expected = ''
    expected = expected + (f'{header}\n' if header is not None else '')
    expected = expected + (f'\n' if header is not None and spacious else '')
    if content1 is not None:
        expected = expected + f'{" " * indent_amount}{content1}'
        expected = expected + (f'{content2}\n' if content2 is not None else '')
        if spacious:
            expected = expected + (f'{" " * indent_amount}\n' if content2 is not None else '\n')
    else:
        expected = expected + (f'{" " * indent_amount}{content2}\n' if content2 is not None else '')
        expected = expected + (f'{" " * indent_amount}\n' if spacious else '')
    assert capsys.readouterr().out == expected


def test_merge_into():
    dst = {}
    src1 = {'k1': 'v1'}
    src2 = {'k2': 'v2'}
    src3 = {'k3': {'v3': 'vv3'}}
    result = merge_into(dst, src1, src2, src3)
    assert result is dst
    assert result['k1'] == 'v1'
    assert result['k2'] == 'v2'
    assert isinstance(result['k3'], dict)
    assert result['k3']['v3'] == 'vv3'

    result = merge(src1, src2, src3)
    assert result is not dst
    assert result is not src1
    assert result is not src2
    assert result is not src3
    assert result['k1'] == 'v1'
    assert result['k2'] == 'v2'
    assert isinstance(result['k3'], dict)
    assert result['k3']['v3'] == 'vv3'
    assert 'k1' in src1
    assert 'k1' not in src2
    assert 'k1' not in src3
    assert 'k2' not in src1
    assert 'k2' in src2
    assert 'k2' not in src3
    assert 'k3' not in src1
    assert 'k3' not in src2
    assert 'k3' in src3
