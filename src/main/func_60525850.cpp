extern "C" int func_60525850(unsigned char* p, unsigned int bit)
{
    unsigned int word = bit >> 5;
    unsigned int shift = bit & 0x1f;
    unsigned int* q = (unsigned int*)(p + word * 4);
    unsigned int v = *(unsigned int*)((char*)q + 0x3614);
    v &= (1u << shift);
    if (v != 0) return 1;
    return 0;
}