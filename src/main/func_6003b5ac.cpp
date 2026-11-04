extern "C" int func_6003b5ac(const unsigned char *base)
{
    unsigned int i;
    for (i = 0; i <= 0x9f; i++) {
        unsigned int bit = i + 0x27d;
        unsigned int word = *(const unsigned int *)(base + ((bit >> 5) << 2) + 0xed0);
        if (word & (1u << (bit & 0x1f)))
            return 1;
    }
    return 0;
}