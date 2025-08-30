from app import create_app
import sass

app = create_app()

if __name__ == "__main__":
    # SCSS -> CSS
    sass.compile(
        dirname=('static/scss', 'static/css'),
        output_style='compressed'
    )
    app.run(debug=True, port=5001)
