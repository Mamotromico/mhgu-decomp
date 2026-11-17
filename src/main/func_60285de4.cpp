extern "C" void func_60285de4(char *p, unsigned bit)
{
    unsigned word = *(unsigned *)(p + (bit >> 5) * 4 + 0x1414);
    word |= 1u << (bit & 0x1f);
    *(unsigned *)(p + (bit >> 5) * 4 + 0x1414) = word;
}