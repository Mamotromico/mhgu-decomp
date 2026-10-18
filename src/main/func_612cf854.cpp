struct func_612cf854_ctx {
    unsigned char pad[0x58];
    void **field;
};

extern "C" void *func_612cf854(struct func_612cf854_ctx *p, unsigned int i)
{
    return p->field[i];
}