struct Sub_61128944 {
    unsigned char pad[0x3c8];
    unsigned int flags;
};

struct Main_61128944 {
    unsigned char pad[0x3328];
    Sub_61128944 *sub;
};

extern "C" Sub_61128944 *func_61128944(Main_61128944 *m, unsigned int mask)
{
    Sub_61128944 *s = m->sub;
    s->flags &= ~mask;
    return s;
}