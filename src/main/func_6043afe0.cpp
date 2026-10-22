struct S {
    unsigned int pad;
    unsigned int low : 8;
    unsigned int target : 16;
    unsigned int high : 8;
};

extern "C" void func_6043afe0(S* s) {
    s->target = 2;
}