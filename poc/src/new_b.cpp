// Count set bits over 0x63 positions of a word array at +0x108 (word index 0x42).
extern "C" int count_bits(unsigned int* self) {
    int n = 0;
    for (unsigned int i = 0; i < 0x63; i++) {
        if (self[0x42 + (i >> 5)] & (1u << (i & 31)))
            n++;
    }
    return n;
}
