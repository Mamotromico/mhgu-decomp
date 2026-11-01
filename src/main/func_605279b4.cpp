struct container {
    char pad[0x4408];
    unsigned long long value;
};

extern "C" unsigned long long func_605279b4(container* p) {
    return p->value;
}