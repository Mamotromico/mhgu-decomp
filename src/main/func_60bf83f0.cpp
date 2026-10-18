struct func_60bf83f0_in {
    void *ptr;
};

struct func_60bf83f0_out {
    unsigned char pad[0x94];
    void *ptr;
};

extern "C" void *func_60bf83f0(struct func_60bf83f0_in *in)
{
    return ((struct func_60bf83f0_out *)in->ptr)->ptr;
}