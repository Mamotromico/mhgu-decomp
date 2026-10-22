struct buf {
    unsigned char pad0[4];
    unsigned int  value;   /* offset 0x4 */
};

extern "C" void func_6122b23c(buf *p, unsigned int amount)
{
    unsigned int v = p->value;
    if (v <= amount)
        p->value = 0;
    else
        p->value = v - amount;
}