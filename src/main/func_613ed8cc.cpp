extern "C" void func_613ed8cc(void *p)
{
    unsigned char *b = (unsigned char *)p;
    unsigned v = ((unsigned)b[0x10] << 24) | ((unsigned)b[0x11] << 16) |
                 ((unsigned)b[0x12] << 8) | (unsigned)b[0x13];
    *(unsigned *)(b + 0x4) = v;
    b[0x8] = b[0x14];
    b[0x9] = b[0x15];
    *(unsigned short *)(b + 0xa) = (unsigned short)(((unsigned)b[0x16] << 8) | b[0x17]);
    *(unsigned short *)(b + 0xc) = (unsigned short)(((unsigned)b[0x18] << 8) | b[0x19]);
    *(unsigned short *)(b + 0xe) = (unsigned short)(((unsigned)b[0x1a] << 8) | b[0x1b]);
}