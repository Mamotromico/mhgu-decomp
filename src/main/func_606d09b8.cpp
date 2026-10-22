struct s_606d09b8 {
    unsigned char pad[0x188c];
    unsigned short f;          /* +0x188c */
    unsigned char tail[2];
};

extern "C" int func_606d09b8(struct s_606d09b8 *p, int v)
{
    return p->f == v;
}