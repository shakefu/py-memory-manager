import pytest

from py_memory_manager import (
    Block,
    MemoryManager,
    MemoryManagerError,
    OutOfMemoryError,
    create_buffer,
)


def test_py_memory_manager():
    assert True


def test_it_initializes_with_all_bytes_free():
    buf = create_buffer(255)
    mm = MemoryManager(buf)
    assert len(mm.free_blocks) == 1
    assert mm.free_blocks[0].offset == 0
    assert mm.free_blocks[0].end == len(buf)


def test_it_allocates_memory_from_the_free_list():
    buf = create_buffer(255)
    mm = MemoryManager(buf)
    alloc = mm.alloc(100)
    assert len(mm.free_blocks) == 1
    assert mm.free_blocks[0].offset == 100
    assert mm.free_blocks[0].end == len(buf)
    assert alloc == buf[:100]


def test_underlying_buffer_is_modified_when_assigning_to_allocated_memory():
    buf = create_buffer(255)
    mm = MemoryManager(buf)
    alloc = mm.alloc(5)

    # Copy bytes into allocated memory
    alloc[:4] = b"test"

    # We have one 0 byte at the end of the allocated memory
    assert alloc == b"test\x00"

    # We reflect the changes in the underlying buffer
    assert buf[:4] == b"test"


def test_it_raises_out_of_memory_error_when_allocating_more_memory_than_available():
    buf = create_buffer(255)
    mm = MemoryManager(buf)

    # Can't allocate more than the buffer size
    with pytest.raises(OutOfMemoryError):
        mm.alloc(256)


def test_it_raises_out_of_memory_error_when_no_free_block_is_large_enough():
    buf = create_buffer(255)
    mm = MemoryManager(buf)

    # Consume most of the buffer
    mm.alloc(100)
    mm.alloc(100)

    # We should reflect that the only free block is too small
    assert len(mm.free_blocks) == 1
    assert mm.free_blocks[0].offset == 200
    assert mm.free_blocks[0].end == len(buf)
    assert mm.free_blocks[0].size < 100

    with pytest.raises(OutOfMemoryError):
        mm.alloc(100)


def test_it_can_free_memory():
    buf = create_buffer(255)
    mm = MemoryManager(buf)
    alloc = mm.alloc(100)
    assert len(mm.free_blocks) == 1
    assert mm.free_blocks[0].offset == 100
    assert mm.free_blocks[0].end == len(buf)

    mm.free(alloc)
    assert len(mm.free_blocks) == 1
    assert mm.free_blocks[0].offset == 0
    assert mm.free_blocks[0].end == len(buf)


def test_it_can_consolidate_free_blocks():
    buf = create_buffer(255)
    mm = MemoryManager(buf)
    a = mm.alloc(16)
    b = mm.alloc(16)
    c = mm.alloc(16)
    d = mm.alloc(16)
    e = mm.alloc(16)

    # Free the second block
    mm.free(b)

    # Free the fourth block
    mm.free(d)

    assert len(mm.free_blocks) == 3
    assert mm.free_blocks[2].offset == 80  # 16 bytes * 5 blocks
    assert mm.free_blocks[2].end == len(buf)

    # Free the fifth block
    mm.free(e)

    assert len(mm.free_blocks) == 2
    assert mm.free_blocks[1].offset == 48  # 16 bytes * 3 blocks, d is freed
    assert mm.free_blocks[1].end == len(buf)

    # Free the first block
    mm.free(a)

    assert len(mm.free_blocks) == 2
    assert mm.free_blocks[0].offset == 0
    assert mm.free_blocks[0].end == 32  # 16 bytes * 2 blocks, a+b is freed
    assert mm.free_blocks[1].offset == 48
    assert mm.free_blocks[1].end == len(buf)

    # Free the final block
    mm.free(c)

    assert len(mm.free_blocks) == 1
    assert mm.free_blocks[0].offset == 0
    assert mm.free_blocks[0].end == len(buf)


def test_it_raises_an_error_when_freeing_unowned_memory():
    buf = create_buffer(255)
    mm = MemoryManager(buf)
    buf2 = create_buffer(255)

    mm2 = MemoryManager(buf2)
    alloc = mm2.alloc(100)

    with pytest.raises(MemoryManagerError):
        mm.free(alloc)


def test_unallocated_returns_the_total_available_memory():
    buf = create_buffer(255)
    mm = MemoryManager(buf)
    assert mm.unallocated() == len(buf)

    alloc = mm.alloc(100)
    assert mm.unallocated() == len(buf) - 100

    mm.free(alloc)
    assert mm.unallocated() == len(buf)


def test_available_returns_the_largest_contiguous_available_memory():
    buf = create_buffer(255)
    mm = MemoryManager(buf)
    assert mm.available() == len(buf)

    # Last contiguous block is 155 bytes
    alloc = mm.alloc(100)
    assert mm.available() == 155

    # Last contiguous block is 55 bytes, everything else is alloc'd
    alloc2 = mm.alloc(100)
    assert mm.available() == 55

    # Free the first block, so the first block is the largest at 100 bytes
    mm.free(alloc)
    assert mm.available() == 100

    # Free the second block, returning to the original state
    mm.free(alloc2)
    assert mm.available() == 255


def test_allocated_returns_the_total_allocated_memory():
    buf = create_buffer(255)
    mm = MemoryManager(buf)
    assert mm.allocated() == 0

    alloc = mm.alloc(100)
    assert mm.allocated() == 100

    alloc2 = mm.alloc(100)
    assert mm.allocated() == 200

    mm.free(alloc)
    assert mm.allocated() == 100

    mm.free(alloc2)
    assert mm.allocated() == 0


def test_repr_returns_a_string_representation_of_the_memory_manager():
    buf = create_buffer(255)
    mm = MemoryManager(buf)
    assert repr(mm) == "<MemoryManager(available=255, allocated=0, unallocated=255)>"

    alloc = mm.alloc(100)
    assert repr(mm) == "<MemoryManager(available=155, allocated=100, unallocated=155)>"

    mm.free(alloc)
    assert repr(mm) == "<MemoryManager(available=255, allocated=0, unallocated=255)>"


def test_block_repr_returns_a_string_representation_of_the_block():
    block = Block(0, 100)
    assert repr(block) == "<Block(offset=0, end=100, size=100)>"
