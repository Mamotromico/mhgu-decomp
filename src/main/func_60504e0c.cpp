extern "C" {

extern void *D_6188ca48;

int func_60504e0c(unsigned char *p)
{
    unsigned char *g = (unsigned char *)*(void **)&D_6188ca48;
    unsigned char flag = *(unsigned char *)(g + 0x48);
    int r1 = 0;
    if (flag == 9) {
        unsigned char v = *(unsigned char *)(p + 0x1ac);
        r1 = v & 1;
    }
    return r1;
}

}