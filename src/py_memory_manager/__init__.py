"""
# PyMemoryManager

This module provides a virtual memory manager for allocating and freeing byte
arrays in a provided buffer.

See the [README](../README.md) for more information.
"""


class MemoryManagerError(RuntimeError):
    """Raised when the memory manager encounters a memory error."""


class OutOfMemoryError(MemoryManagerError):
    """Raised when the memory manager runs out of memory."""


class Block:
    """A block of memory.

    This class provides a convenience wrapper around a tuple of offset and end.

    """

    __slots__ = ["offset", "end"]

    def __init__(self, offset: int, end: int):
        self.offset = offset
        self.end = end

    @property
    def size(self) -> int:
        """Return the size of the block."""
        return self.end - self.offset

    def __repr__(self) -> str:
        return f"<Block(offset={self.offset}, end={self.end}, size={self.size})>"


class MemoryManager:
    """
    A virtual memory manager for allocating and freeing byte arrays in a provided buffer.
    """

    buf: memoryview
    alloc_blocks: dict[memoryview, Block]
    free_blocks: list

    def __init__(self, buf: bytearray):
        # Capture reference to the buffer, its contents are not zeroed
        self.buf = memoryview(buf)
        self.alloc_blocks = {}
        # Initialize free list to all bytes in the buffer
        self.free_blocks = [Block(0, len(self.buf))]

    def alloc(self, size: int) -> memoryview:
        """Return a bytearray of the given size from the buffer."""
        if size > len(self.buf):
            raise OutOfMemoryError(
                f"Size {size} is greater than the buffer size {len(self.buf)}"
            )

        # Find the first free block that is large enough
        for i, free_block in enumerate(self.free_blocks):
            if free_block.size >= size:
                # Split the free block into two
                self.free_blocks[i] = Block(free_block.offset + size, free_block.end)

                # Create a memoryview of the allocated memory
                mv = self.buf[free_block.offset : free_block.offset + size]

                # Get the object id of the memoryview, since memoryviews are not hashable
                object_id = id(mv)

                # Add the block to the allocations dictionary
                self.alloc_blocks[object_id] = Block(
                    free_block.offset, free_block.offset + size
                )

                return mv

        raise OutOfMemoryError(
            f"Could not allocate memory of size {size}, not enough contiguous memory"
        )

    def free(self, alloc: memoryview):
        """Free the memory given."""
        # Get the object id we're trying to free
        object_id = id(alloc)

        if object_id not in self.alloc_blocks:
            raise MemoryManagerError(
                f"Alloc is not owned by this memory manager (id: {object_id})"
            )

        # Ensure the memory is released, so it cannot be used again
        alloc.release()

        # Get the block from the allocations dictionary and remove it
        block = self.alloc_blocks.pop(object_id)

        # Add the block to the free list
        self.free_blocks.append(block)

        # Sort the free list by offset, a little costly, but it should mostly
        # stay sorted, and ensures we always can find multiple contiguous free
        # blocks to join if we had segmented memory
        self.free_blocks.sort(key=lambda x: x.offset)

        # Merge adjacent free blocks
        i = 0
        while i < len(self.free_blocks) - 1:
            if self.free_blocks[i].end == self.free_blocks[i + 1].offset:
                self.free_blocks[i] = Block(
                    self.free_blocks[i].offset, self.free_blocks[i + 1].end
                )
                self.free_blocks.pop(i + 1)
            else:
                i += 1

    def unallocated(self) -> int:
        """Return the total available memory in the buffer."""
        return sum(block.size for block in self.free_blocks)

    def available(self) -> int:
        """Return the largest contiguous available memory in the buffer."""
        return max(block.size for block in self.free_blocks)

    def allocated(self) -> int:
        """Return the total allocated memory in the buffer."""
        return sum(block.size for block in self.alloc_blocks.values())

    def __repr__(self) -> str:
        return f"<MemoryManager(available={self.available()}, allocated={self.allocated()}, unallocated={self.unallocated()})>"


def create_buffer(size: int) -> bytearray:
    """Return a mutable bytearray of the given size filled with zero bytes."""
    return bytearray(0 for _ in range(size))
