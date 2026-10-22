struct func_60120eec_arg0 {
    unsigned int pad0;
    void* field4;
};

struct func_60120eec_dispatch {
    unsigned int pad0[3];
    void (*callback)(void*, void*);
};

extern "C" void func_60120eec(func_60120eec_arg0* a, func_60120eec_dispatch** b)
{
    (*(func_60120eec_dispatch**)b)->callback(b, a->field4);
}