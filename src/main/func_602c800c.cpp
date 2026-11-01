extern "C" void func_602c800c(char *p, int a, int b)
{
    typedef struct {
        char pad0[0x2b44];
        unsigned char f_2b44;
        char pad1[0x2b50 - 0x2b44 - 1];
        int f_2b50;
        int f_2b54;
        int f_2b58;
    } S;
    S *s = (S *)p;
    s->f_2b44 = 1;
    s->f_2b50 = a;
    s->f_2b54 = b;
    s->f_2b58 = 0;
}