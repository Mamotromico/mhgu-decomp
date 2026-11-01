struct table_t {
    char pad0[0xd84];
    unsigned int bits[8];
};

extern "C" int func_6052462c(table_t *t, unsigned int idx)
{
    if (idx > 0x38)
        return 0;
    unsigned int word = t->bits[idx >> 5];
    unsigned int mask = 1u << (idx & 0x1f);
    return (word & mask) ? 1 : 0;
}