extern "C" void func_6026fdb8(char *p, unsigned int v, int flag)
{
    *(unsigned int *)(p + 0x510) = v;
    unsigned short h = *(unsigned short *)(p + 0x504);
    h = (unsigned short)(flag != 0 ? (h | 0x4) : (h & 0xfffb));
    *(unsigned short *)(p + 0x504) = h;
}