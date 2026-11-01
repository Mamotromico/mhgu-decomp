extern "C" void func_6025f5b0(char *base, unsigned int idx, unsigned int value)
{
    if (idx > 0x53)
        return;
    unsigned char b = *(unsigned char *)(base + 0x1384e + idx);
    unsigned int *p = (unsigned int *)(base + b * 0x560 + 0x13c38);
    *p |= value;
}