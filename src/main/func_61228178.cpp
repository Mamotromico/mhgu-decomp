struct func_61228178_S {
    unsigned char pad[5];
    unsigned char field;
};

extern "C" int func_61228178(const func_61228178_S* p) {
    return (p->field & 3) == 0;
}