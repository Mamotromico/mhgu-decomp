extern "C" void func_6138f900(void *a0, unsigned char *a1, unsigned int a2, unsigned int a3)
{
    unsigned int *out = (unsigned int *)a0;
    if (*(unsigned int *)(a1 + 0x54) != 0) {
        *out = 0x00010c08;
        return;
    }
    *(unsigned int *)(a1 + 0x54) = a2;
    *(unsigned int *)(a1 + 0x58) = a3;
    *out = 0;
}