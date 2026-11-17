extern "C" void func_60a0a3fc(unsigned char *ctx, unsigned char *out, char *base, unsigned int count);

struct S_ENTRY16 {
    char pad0[0x8];
    char *ptr8;
};

struct S_NODE {
    char pad0[0x8];
    char *ptr8;
    unsigned short a;
    char pad1[0x2];
    unsigned short b;
    char pad2[0xa];
    char *ptr1c;
};

extern "C" void func_60a0a3fc(unsigned char *ctx, unsigned char *out, char *base, unsigned int count)
{
    if (count != 0) {
        unsigned int i = 0;
        do {
            S_ENTRY16 *e = (S_ENTRY16 *)(base + i * 0x10);
            char *p = e->ptr8;
            S_NODE *q = (S_NODE *)*(char **)(p + 0x8);
            unsigned int k;
            for (k = q->a; k < q->b; k++)
                out[k] = 0;

            if (i == 0) {
                char *r = q->ptr1c;
                if (r != 0) {
                    unsigned int k2;
                    for (k2 = *(unsigned short *)(r + 0xe); k2 < *(unsigned short *)(r + 0x10); k2++)
                        out[k2] = 0;
                }
            }
            i++;
        } while (i != count);
    }
}