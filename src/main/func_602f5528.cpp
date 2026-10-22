extern "C" unsigned int* func_602f5528(unsigned char* base, unsigned int bit)
{
    unsigned int* p = (unsigned int*)(base + 0x2974);
    *p |= 1u << bit;
    return p;
}