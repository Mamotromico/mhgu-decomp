extern "C" void func_6087b878(unsigned char *p)
{
    *(unsigned int *)(p + 0x54) |= 0x100;
    *(unsigned int *)(p + 0x68) = *(unsigned int *)(p + 0x40);
    *(unsigned int *)(p + 0x6c) = 0;
    unsigned int v = *(unsigned int *)(p + 0x19c);
    v &= ~(1u << 0xc);
    *(unsigned int *)(p + 0x19c) = v;
}