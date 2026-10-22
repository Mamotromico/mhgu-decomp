struct Data {
    double value;
    int code;
};

extern "C" double func_6122faa4(const Data *p) {
    if (p->code == 2) {
        return p->value;
    }
    return 0.0;
}