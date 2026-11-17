extern "C" {

extern char D_62143990[];

void func_613a3634(void *p, unsigned short v)
{
    *(unsigned short *)((char *)p + 0x1e) = v & 0xfffe;
    *(unsigned short *)(D_62143990 + 0x96) = v & 0xfffe;
}

}