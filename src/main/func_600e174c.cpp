extern "C" void func_600e174c(unsigned char *base, int index, unsigned short value)
{
    *(unsigned short *)(base + index * 2 + 0x31c) = value;
}