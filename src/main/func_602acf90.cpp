extern "C" void func_602acf90(char *base)
{
    unsigned int *p = (unsigned int *)(base + 0x2b70);
    unsigned int v = *p;
    v = (v & ~(0x7u << 16)) | (0u << 16);
    *p = v;
}